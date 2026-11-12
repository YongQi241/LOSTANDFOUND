-- Executable integrity/privacy reference for PA3, PostgreSQL 15+.
-- Apply schema.sql first. This is not an automatic production migration.
-- SECURITY DEFINER owners must be migration-only, never the API login.

CREATE FUNCTION app.user_can_interact(p_user uuid) RETURNS boolean
LANGUAGE sql STABLE SET search_path = pg_catalog AS $$
  SELECT EXISTS (SELECT 1 FROM app.users
    WHERE user_id = p_user AND status = 'ACTIVE' AND is_verified);
$$;

CREATE FUNCTION app.guard_post() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF NEW.incident_at > clock_timestamp() THEN
    RAISE EXCEPTION 'incident date is in the future' USING ERRCODE='23514';
  END IF;
  IF TG_OP = 'INSERT' THEN
    IF NEW.status <> 'ACTIVE' OR NOT app.user_can_interact(NEW.owner_id) THEN
      RAISE EXCEPTION 'new post needs verified active owner and ACTIVE state' USING ERRCODE='23514';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM app.campuses c JOIN app.universities u USING(university_id)
      WHERE c.campus_id=NEW.campus_id AND c.is_active AND u.status='APPROVED')
      OR NOT EXISTS (SELECT 1 FROM app.categories WHERE category_id=NEW.category_id AND is_active) THEN
      RAISE EXCEPTION 'unavailable campus/category' USING ERRCODE='23514';
    END IF;
  ELSE
    IF (NEW.post_id,NEW.owner_id,NEW.post_type) IS DISTINCT FROM (OLD.post_id,OLD.owner_id,OLD.post_type) THEN
      RAISE EXCEPTION 'post identity, owner and type are immutable' USING ERRCODE='23514';
    END IF;
    IF OLD.status <> 'ACTIVE' AND (NEW.title,NEW.description,NEW.location_detail,
      NEW.campus_id,NEW.category_id,NEW.incident_at,NEW.verification_question,NEW.reward_amount)
      IS DISTINCT FROM (OLD.title,OLD.description,OLD.location_detail,OLD.campus_id,
      OLD.category_id,OLD.incident_at,OLD.verification_question,OLD.reward_amount) THEN
      RAISE EXCEPTION 'non-ACTIVE post content is read-only' USING ERRCODE='23514';
    END IF;
    IF NEW.verification_question IS DISTINCT FROM OLD.verification_question
      AND EXISTS (SELECT 1 FROM app.claims WHERE post_id=OLD.post_id AND status='PENDING') THEN
      RAISE EXCEPTION 'cannot change question with pending claims' USING ERRCODE='23514';
    END IF;
    IF NEW.status <> OLD.status AND NOT (
      (OLD.status='ACTIVE' AND NEW.status IN ('RESOLVED','REPORTED','CLOSED')) OR
      (OLD.status='RESOLVED' AND NEW.status='REPORTED') OR
      (OLD.status='REPORTED' AND (NEW.status=OLD.previous_status OR NEW.status='CLOSED'))) THEN
      RAISE EXCEPTION 'illegal Post transition' USING ERRCODE='23514';
    END IF;
    IF NEW.status='REPORTED' AND (NEW.previous_status IS DISTINCT FROM
      CASE WHEN OLD.status='REPORTED' THEN OLD.previous_status ELSE OLD.status END) THEN
      RAISE EXCEPTION 'wrong state snapshot' USING ERRCODE='23514';
    END IF;
    IF NEW.status='CLOSED' AND OLD.status<>'CLOSED' AND NOT (
      (OLD.status='ACTIVE' AND NEW.close_reason='OWNER_DELETED') OR
      (OLD.status='REPORTED' AND NEW.close_reason='ADMIN_REMOVED')) THEN
      RAISE EXCEPTION 'wrong close reason for state' USING ERRCODE='23514';
    END IF;
    NEW.updated_at := clock_timestamp();
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER post_guard BEFORE INSERT OR UPDATE ON app.posts
FOR EACH ROW EXECUTE FUNCTION app.guard_post();

CREATE FUNCTION app.guard_claim() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
DECLARE p app.posts;
BEGIN
  SELECT * INTO p FROM app.posts WHERE post_id=NEW.post_id FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'post missing' USING ERRCODE='23503'; END IF;
  IF TG_OP='UPDATE' THEN
    IF (NEW.claim_id,NEW.post_id,NEW.claimant_id,NEW.security_answer,NEW.claim_message,
        NEW.proof_object_key,NEW.proof_mime_type,NEW.proof_size_bytes,NEW.submitted_at)
       IS DISTINCT FROM (OLD.claim_id,OLD.post_id,OLD.claimant_id,OLD.security_answer,
        OLD.claim_message,OLD.proof_object_key,OLD.proof_mime_type,OLD.proof_size_bytes,OLD.submitted_at) THEN
      RAISE EXCEPTION 'Claim evidence and identity are immutable' USING ERRCODE='23514';
    END IF;
    IF OLD.status<>'PENDING' OR NEW.status NOT IN ('ACCEPTED','REJECTED','CANCELLED') THEN
      RAISE EXCEPTION 'illegal Claim transition' USING ERRCODE='23514';
    END IF;
  ELSE
    IF NEW.status<>'PENDING' OR p.status<>'ACTIVE' THEN
      RAISE EXCEPTION 'new Claim requires ACTIVE post and PENDING state' USING ERRCODE='23514';
    END IF;
  END IF;
  IF NEW.claimant_id=p.owner_id THEN
    RAISE EXCEPTION 'self claim forbidden' USING ERRCODE='23514';
  END IF;
  IF (TG_OP='INSERT' OR NEW.status='ACCEPTED') AND
     (NOT app.user_can_interact(NEW.claimant_id) OR NOT app.user_can_interact(p.owner_id) OR p.status<>'ACTIVE') THEN
    RAISE EXCEPTION 'inactive/unverified party or closed claim window' USING ERRCODE='23514';
  END IF;
  IF p.post_type='FOUND' AND nullif(btrim(NEW.security_answer),'') IS NULL THEN
    RAISE EXCEPTION 'FOUND requires security answer' USING ERRCODE='23514';
  END IF;
  IF p.post_type='LOST' AND nullif(btrim(NEW.claim_message),'') IS NULL AND NEW.proof_object_key IS NULL THEN
    RAISE EXCEPTION 'LOST requires message or proof' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER claim_guard BEFORE INSERT OR UPDATE ON app.claims
FOR EACH ROW EXECUTE FUNCTION app.guard_claim();

CREATE FUNCTION app.guard_image() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
DECLARE id uuid; st text;
BEGIN
  id := CASE WHEN TG_OP='DELETE' THEN OLD.post_id ELSE NEW.post_id END;
  SELECT status INTO st FROM app.posts WHERE post_id=id FOR UPDATE;
  IF st IS DISTINCT FROM 'ACTIVE' THEN
    RAISE EXCEPTION 'images editable only on ACTIVE post' USING ERRCODE='23514';
  END IF;
  IF TG_OP='UPDATE' AND NEW.post_id<>OLD.post_id THEN
    RAISE EXCEPTION 'cannot move image to another post' USING ERRCODE='23514';
  END IF;
  IF TG_OP='DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER image_guard BEFORE INSERT OR UPDATE OR DELETE ON app.post_images
FOR EACH ROW EXECUTE FUNCTION app.guard_image();

-- Cross-row assertions run at COMMIT, allowing legitimate multi-row transactions.
CREATE FUNCTION app.assert_post_complete() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE id uuid; p app.posts; n integer;
BEGIN
  id := CASE WHEN TG_OP='DELETE' THEN OLD.post_id ELSE NEW.post_id END;
  SELECT * INTO p FROM app.posts WHERE post_id=id;
  IF NOT FOUND THEN RETURN NULL; END IF;
  SELECT count(*) INTO n FROM app.post_images WHERE post_id=id;
  IF n NOT BETWEEN 1 AND 5 OR NOT EXISTS (SELECT 1 FROM private.post_details WHERE post_id=id) THEN
    RAISE EXCEPTION 'post requires contact and 1..5 images at commit' USING ERRCODE='23514';
  END IF;
  IF EXISTS (SELECT 1 FROM app.claims WHERE post_id=id AND status='ACCEPTED') AND
     NOT (p.status='RESOLVED' OR (p.status='REPORTED' AND p.previous_status='RESOLVED') OR
          (p.status='CLOSED' AND p.close_reason='ADMIN_REMOVED')) THEN
    RAISE EXCEPTION 'accepted Claim must resolve its post' USING ERRCODE='23514';
  END IF;
  IF (p.status IN ('RESOLVED','CLOSED') OR (p.status='REPORTED' AND p.previous_status='RESOLVED'))
     AND EXISTS (SELECT 1 FROM app.claims WHERE post_id=id AND status='PENDING') THEN
    RAISE EXCEPTION 'resolved/closed post cannot retain pending Claims' USING ERRCODE='23514';
  END IF;
  RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER post_complete AFTER INSERT OR UPDATE ON app.posts
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION app.assert_post_complete();
CREATE CONSTRAINT TRIGGER image_complete AFTER INSERT OR UPDATE OR DELETE ON app.post_images
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION app.assert_post_complete();
CREATE CONSTRAINT TRIGGER contact_complete AFTER INSERT OR UPDATE OR DELETE ON private.post_details
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION app.assert_post_complete();
CREATE CONSTRAINT TRIGGER claim_complete AFTER INSERT OR UPDATE OR DELETE ON app.claims
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION app.assert_post_complete();

CREATE FUNCTION app.assert_user_contact() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE id uuid;
BEGIN
  id := CASE WHEN TG_OP='DELETE' THEN OLD.user_id ELSE NEW.user_id END;
  IF EXISTS (SELECT 1 FROM app.users WHERE user_id=id) AND
     NOT EXISTS (SELECT 1 FROM private.user_contacts WHERE user_id=id) THEN
    RAISE EXCEPTION 'profile requires school contact at commit' USING ERRCODE='23514';
  END IF;
  RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER profile_contact AFTER INSERT OR UPDATE ON app.users
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION app.assert_user_contact();
CREATE CONSTRAINT TRIGGER user_contact_complete AFTER INSERT OR UPDATE OR DELETE ON private.user_contacts
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION app.assert_user_contact();

CREATE FUNCTION app.guard_audit() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF TG_OP<>'INSERT' THEN RAISE EXCEPTION 'audit is append only' USING ERRCODE='23514'; END IF;
  IF NOT EXISTS (SELECT 1 FROM app.users WHERE user_id=NEW.admin_id AND role='ADMIN'
    AND status='ACTIVE' AND is_verified) THEN
    RAISE EXCEPTION 'audit actor must be active Admin' USING ERRCODE='42501';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER audit_guard BEFORE INSERT OR UPDATE OR DELETE ON app.moderation_actions
FOR EACH ROW EXECUTE FUNCTION app.guard_audit();

-- Deliberate context replicas documented in the 3NF review. Their determinants
-- (Claim.post_id and moderation action contents) are immutable.
CREATE FUNCTION app.guard_notification_context() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF NEW.claim_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM app.claims WHERE claim_id=NEW.claim_id AND post_id=NEW.post_id) THEN
    RAISE EXCEPTION 'notification Claim/Post mismatch' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER notification_context_guard BEFORE INSERT OR UPDATE ON app.notifications
FOR EACH ROW EXECUTE FUNCTION app.guard_notification_context();

CREATE FUNCTION app.guard_report_settlement() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
  IF NEW.action_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM app.moderation_actions a WHERE a.action_id=NEW.action_id
      AND a.post_id=NEW.post_id AND
      ((a.action='KEEP_POST' AND NEW.status='DISMISSED') OR
       (a.action='REMOVE_POST' AND NEW.status='APPROVED'))) THEN
    RAISE EXCEPTION 'report settlement must match audit Post and decision' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER report_settlement_guard BEFORE INSERT OR UPDATE ON app.reports
FOR EACH ROW EXECUTE FUNCTION app.guard_report_settlement();

-- Allowlist projection: no contact, email, answer, proof key, private identifier or storage location.
CREATE VIEW app.public_posts WITH (security_barrier=true) AS
SELECT p.post_id,p.post_type,p.title,p.description,p.location_detail,p.incident_at,
       p.campus_id,p.category_id,p.status,p.verification_question,p.reward_amount,p.created_at
FROM app.posts p JOIN app.users u ON u.user_id=p.owner_id
WHERE p.status IN ('ACTIVE','RESOLVED') AND u.status='ACTIVE';

CREATE FUNCTION app.write_post_contact(p_actor uuid,p_post uuid,p_kind text,p_value text,
  p_identifier text DEFAULT NULL,p_location text DEFAULT NULL) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE p app.posts;
BEGIN
  SELECT * INTO p FROM app.posts WHERE post_id=p_post FOR UPDATE;
  IF NOT FOUND OR p.owner_id<>p_actor OR p.status<>'ACTIVE' OR NOT app.user_can_interact(p_actor) THEN
    RAISE EXCEPTION 'contact write forbidden' USING ERRCODE='42501';
  END IF;
  IF (p.post_type='FOUND' AND p_identifier IS NOT NULL) OR (p.post_type='LOST' AND p_location IS NOT NULL) THEN
    RAISE EXCEPTION 'wrong private subtype attribute' USING ERRCODE='23514';
  END IF;
  INSERT INTO private.post_details VALUES (p_post,p_kind,p_value,p_identifier,p_location)
  ON CONFLICT (post_id) DO UPDATE SET contact_kind=EXCLUDED.contact_kind,
    contact_value=EXCLUDED.contact_value,private_identifier=EXCLUDED.private_identifier,
    storage_location=EXCLUDED.storage_location;
END $$;

CREATE FUNCTION app.read_post_contact(p_viewer uuid,p_post uuid)
RETURNS TABLE(contact_kind text,contact_value text)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE p app.posts;
BEGIN
  SELECT * INTO p FROM app.posts WHERE post_id=p_post;
  IF NOT FOUND OR NOT app.user_can_interact(p_viewer) THEN
    RAISE EXCEPTION 'contact read forbidden' USING ERRCODE='42501';
  END IF;
  IF p.owner_id<>p_viewer AND NOT (p.status='RESOLVED' AND app.user_can_interact(p.owner_id)
    AND EXISTS (SELECT 1 FROM app.claims c WHERE c.post_id=p_post
      AND c.claimant_id=p_viewer AND c.status='ACCEPTED')) THEN
    RAISE EXCEPTION 'Claim not accepted for this viewer' USING ERRCODE='42501';
  END IF;
  RETURN QUERY SELECT d.contact_kind::text,d.contact_value::text FROM private.post_details d WHERE d.post_id=p_post;
END $$;

CREATE FUNCTION app.read_claimant_contact(p_viewer uuid,p_claim uuid)
RETURNS TABLE(contact_kind text,contact_value text)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE c app.claims; p app.posts;
BEGIN
  SELECT * INTO c FROM app.claims WHERE claim_id=p_claim;
  SELECT * INTO p FROM app.posts WHERE post_id=c.post_id;
  IF c.claim_id IS NULL OR p.owner_id<>p_viewer OR c.status<>'ACCEPTED' OR p.status<>'RESOLVED'
    OR NOT app.user_can_interact(p_viewer) OR NOT app.user_can_interact(c.claimant_id) THEN
    RAISE EXCEPTION 'claimant contact forbidden' USING ERRCODE='42501';
  END IF;
  RETURN QUERY SELECT 'EMAIL'::text,d.university_email::text FROM private.user_contacts d WHERE d.user_id=c.claimant_id;
END $$;

CREATE FUNCTION app.submit_claim(p_actor uuid,p_post uuid,p_answer text DEFAULT NULL,p_message text DEFAULT NULL,
 p_key text DEFAULT NULL,p_mime text DEFAULT NULL,p_size integer DEFAULT NULL)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE p app.posts; cid uuid;
BEGIN
  SELECT * INTO p FROM app.posts WHERE post_id=p_post;
  PERFORM 1 FROM app.users WHERE user_id IN (p_actor,p.owner_id) ORDER BY user_id FOR UPDATE;
  SELECT * INTO p FROM app.posts WHERE post_id=p_post FOR UPDATE;
  IF p.post_id IS NULL THEN RAISE EXCEPTION 'post missing' USING ERRCODE='P0002'; END IF;
  INSERT INTO app.claims(post_id,claimant_id,security_answer,claim_message,
    proof_object_key,proof_mime_type,proof_size_bytes)
  VALUES(p_post,p_actor,p_answer,p_message,p_key,p_mime,p_size) RETURNING claim_id INTO cid;
  INSERT INTO app.notifications(recipient_id,post_id,claim_id,event_type,message_code)
    VALUES(p.owner_id,p_post,cid,'CLAIM_RECEIVED','CLAIM_RECEIVED');
  RETURN cid;
END $$;

CREATE FUNCTION app.decide_claim(p_actor uuid,p_claim uuid,p_decision text,p_reason text DEFAULT NULL)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE c app.claims; p app.posts; decision_time timestamptz := clock_timestamp();
BEGIN
  SELECT * INTO c FROM app.claims WHERE claim_id=p_claim;
  SELECT * INTO p FROM app.posts WHERE post_id=c.post_id;
  IF c.claim_id IS NULL THEN RAISE EXCEPTION 'Claim missing' USING ERRCODE='P0002'; END IF;
  PERFORM 1 FROM app.users WHERE user_id IN (p_actor,p.owner_id,c.claimant_id) ORDER BY user_id FOR UPDATE;
  SELECT * INTO p FROM app.posts WHERE post_id=p.post_id FOR UPDATE;
  SELECT * INTO c FROM app.claims WHERE claim_id=p_claim;
  IF p.owner_id<>p_actor OR NOT app.user_can_interact(p_actor) THEN
    RAISE EXCEPTION 'only owner decides' USING ERRCODE='42501';
  END IF;
  IF p.status<>'ACTIVE' OR c.status<>'PENDING' OR p_decision IS NULL OR p_decision NOT IN ('ACCEPT','REJECT') THEN
    RAISE EXCEPTION 'Claim decision conflict' USING ERRCODE='P0001';
  END IF;
  IF p_decision='ACCEPT' THEN
    IF NOT app.user_can_interact(c.claimant_id) THEN RAISE EXCEPTION 'Claimant unavailable' USING ERRCODE='23514'; END IF;
    UPDATE app.claims SET status='ACCEPTED',decided_at=decision_time WHERE claim_id=p_claim;
    UPDATE app.posts SET status='RESOLVED' WHERE post_id=p.post_id;
    WITH changed AS (
      UPDATE app.claims SET status='REJECTED',decided_at=decision_time,decision_reason='OTHER_CLAIM_ACCEPTED'
      WHERE post_id=p.post_id AND claim_id<>p_claim AND status='PENDING' RETURNING *
    ) INSERT INTO app.notifications(recipient_id,post_id,claim_id,event_type,message_code)
      SELECT claimant_id,post_id,claim_id,'CLAIM_DECIDED','CLAIM_REJECTED' FROM changed;
  ELSE
    UPDATE app.claims SET status='REJECTED',decided_at=decision_time,decision_reason=p_reason WHERE claim_id=p_claim;
  END IF;
  INSERT INTO app.notifications(recipient_id,post_id,claim_id,event_type,message_code)
  VALUES (c.claimant_id,p.post_id,c.claim_id,'CLAIM_DECIDED',CASE WHEN p_decision='ACCEPT' THEN 'CLAIM_ACCEPTED' ELSE 'CLAIM_REJECTED' END);
END $$;

CREATE FUNCTION app.report_post(p_actor uuid,p_post uuid,p_reason text,p_detail text DEFAULT NULL)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE p app.posts; rid uuid; n integer;
BEGIN
  SELECT * INTO p FROM app.posts WHERE post_id=p_post;
  PERFORM 1 FROM app.users WHERE user_id IN (p_actor,p.owner_id) ORDER BY user_id FOR UPDATE;
  SELECT * INTO p FROM app.posts WHERE post_id=p_post FOR UPDATE;
  IF p.post_id IS NULL OR p.status='CLOSED' OR p.owner_id=p_actor OR NOT app.user_can_interact(p_actor) THEN
    RAISE EXCEPTION 'report forbidden' USING ERRCODE='42501';
  END IF;
  INSERT INTO app.reports(post_id,reporter_id,reason,detail_message)
    VALUES(p_post,p_actor,p_reason,p_detail) RETURNING report_id INTO rid;
  SELECT count(*) INTO n FROM app.reports WHERE post_id=p_post AND status='PENDING';
  IF n>=3 AND p.status<>'REPORTED' THEN
    UPDATE app.posts SET previous_status=status,status='REPORTED' WHERE post_id=p_post;
    INSERT INTO app.notifications(recipient_id,post_id,event_type,message_code)
      VALUES(p.owner_id,p_post,'POST_MODERATED','POST_REPORTED');
  END IF;
  RETURN rid;
END $$;

CREATE FUNCTION app.review_post(p_admin uuid,p_post uuid,p_decision text,p_reason text DEFAULT NULL)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE p app.posts; aid uuid; decision_time timestamptz := clock_timestamp();
BEGIN
  SELECT * INTO p FROM app.posts WHERE post_id=p_post;
  PERFORM 1 FROM app.users WHERE user_id IN (p_admin,p.owner_id) ORDER BY user_id FOR UPDATE;
  IF NOT EXISTS (SELECT 1 FROM app.users WHERE user_id=p_admin AND role='ADMIN'
    AND status='ACTIVE' AND is_verified) THEN RAISE EXCEPTION 'Admin required' USING ERRCODE='42501'; END IF;
  SELECT * INTO p FROM app.posts WHERE post_id=p_post FOR UPDATE;
  IF p.post_id IS NULL OR p.status<>'REPORTED' OR p_decision IS NULL OR p_decision NOT IN ('KEEP','REMOVE') THEN
    RAISE EXCEPTION 'review conflict' USING ERRCODE='P0001';
  END IF;
  INSERT INTO app.moderation_actions(admin_id,post_id,action,reason)
    VALUES(p_admin,p_post,CASE WHEN p_decision='KEEP' THEN 'KEEP_POST' ELSE 'REMOVE_POST' END,p_reason)
    RETURNING action_id INTO aid;
  UPDATE app.reports SET status=CASE WHEN p_decision='KEEP' THEN 'DISMISSED' ELSE 'APPROVED' END,action_id=aid
    WHERE post_id=p_post AND status='PENDING';
  IF p_decision='KEEP' THEN
    UPDATE app.posts SET status=previous_status,previous_status=NULL WHERE post_id=p_post;
  ELSE
    UPDATE app.posts SET status='CLOSED',previous_status=NULL,close_reason='ADMIN_REMOVED',
      closure_note=p_reason,closed_at=decision_time WHERE post_id=p_post;
    WITH changed AS (
      UPDATE app.claims SET status='CANCELLED',decision_reason='POST_REMOVED',decided_at=decision_time
        WHERE post_id=p_post AND status='PENDING' RETURNING *
    ) INSERT INTO app.notifications(recipient_id,post_id,claim_id,event_type,message_code)
      SELECT claimant_id,post_id,claim_id,'CLAIM_DECIDED','CLAIM_CANCELLED' FROM changed;
  END IF;
  INSERT INTO app.notifications(recipient_id,post_id,event_type,message_code)
    VALUES(p.owner_id,p_post,'POST_MODERATED',CASE WHEN p_decision='KEEP' THEN 'POST_KEPT' ELSE 'POST_REMOVED' END);
END $$;

-- No direct browser/Data API access: all requests go through the trusted Express API.
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='lf_api') THEN CREATE ROLE lf_api NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='lf_auth') THEN CREATE ROLE lf_auth NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='lf_catalog') THEN CREATE ROLE lf_catalog NOLOGIN; END IF;
END $$;
GRANT lf_api TO lf_auth;
GRANT lf_api TO lf_catalog;
REVOKE ALL ON SCHEMA app,private FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA app,private FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA app FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA app REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
GRANT USAGE ON SCHEMA app TO lf_api;
GRANT SELECT,INSERT,UPDATE ON ALL TABLES IN SCHEMA app TO lf_api;
REVOKE UPDATE ON app.moderation_actions FROM lf_api;
-- No DELETE grant: lifecycle changes preserve history. API roles cannot SELECT private.*.
GRANT USAGE ON SCHEMA private TO lf_auth;
GRANT SELECT(user_id,university_email,email_domain),INSERT,UPDATE ON private.user_contacts TO lf_auth;
GRANT USAGE ON SCHEMA private TO lf_catalog;
GRANT SELECT,INSERT,UPDATE ON private.school_requests,private.school_request_campuses TO lf_catalog;
GRANT EXECUTE ON FUNCTION app.user_can_interact(uuid),
 app.write_post_contact(uuid,uuid,text,text,text,text),app.read_post_contact(uuid,uuid),
 app.read_claimant_contact(uuid,uuid),app.submit_claim(uuid,uuid,text,text,text,text,integer),app.decide_claim(uuid,uuid,text,text),
 app.report_post(uuid,uuid,text,text),app.review_post(uuid,uuid,text,text) TO lf_api;
-- Guard functions are invoked by triggers and may read profiles during writes.
GRANT EXECUTE ON FUNCTION app.guard_post(),app.guard_claim(),app.guard_image(),app.guard_audit() TO lf_api;

-- Defense in depth for future exposure: only the trusted backend role has policies.
DO $$ DECLARE r record; BEGIN
  FOR r IN SELECT schemaname,tablename FROM pg_tables WHERE schemaname IN ('app','private') LOOP
    EXECUTE format('ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY',r.schemaname,r.tablename);
    EXECUTE format('CREATE POLICY backend_only ON %I.%I TO lf_api USING (true) WITH CHECK (true)',r.schemaname,r.tablename);
  END LOOP;
END $$;
-- lf_auth sees only school email, never phone_number. Contact functions return only kind/value.
-- Their UUID arguments are NOT authentication: the API must derive actor/viewer from verified
-- identity and never accept them from request body. Never grant these functions to anon/authenticated.
