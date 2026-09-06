-- DEV-only, metadata-only observer. No payload values, SQL text or credentials.
SET default_transaction_read_only = on;
SET statement_timeout = '2s';
SELECT jsonb_build_object(
 'at',clock_timestamp(),
 'outbox',(SELECT jsonb_agg(jsonb_build_object(
  'id',id,'status',status,'attempts',attempts,'created_at',created_at,
  'next_attempt_at',next_attempt_at,'locked_at',locked_at,
  'first_claimed_at',first_claimed_at,'processed_at',processed_at,
  'completed_keys',payload_json#>'{managed_config_progress,completed_keys}',
  'tee_written_key',payload_json#>'{managed_config_progress,tee_written_key}',
  'stage_attempts',payload_json#>'{managed_config_progress,stage_attempts}'))
  FROM paas_outbox_events WHERE org_id=:'org_id'::uuid
   AND event_type='paas.template.managed_config.deliver'
   AND payload_json->>'instance_name'=:'app_name'),
 'app',(SELECT jsonb_agg(jsonb_build_object('id',id,'status',status,'created_at',created_at))
   FROM hosted_apps WHERE org_id=:'org_id'::uuid AND name=:'app_name'),
 'deployments',(SELECT jsonb_agg(jsonb_build_object('id',d.id,'status',d.status,
   'created_at',d.created_at,'updated_at',d.updated_at,'observed_at',d.observed_at,
   'last_reconciliation_attempted_at',d.last_reconciliation_attempted_at,
   'last_successful_reconciled_at',d.last_successful_reconciled_at))
   FROM hosted_deployments d JOIN hosted_apps a ON a.id=d.hosted_app_id
   WHERE a.org_id=:'org_id'::uuid AND a.name=:'app_name'),
 'db_waits',(SELECT jsonb_agg(jsonb_build_object('state',state,'type',wait_event_type,
   'event',wait_event,'count',n)) FROM (
   SELECT state,wait_event_type,wait_event,count(*) n FROM pg_stat_activity
   WHERE datname='enclava_paas' AND pid<>pg_backend_pid()
   GROUP BY state,wait_event_type,wait_event) w));
\watch 0.5 c=1800
