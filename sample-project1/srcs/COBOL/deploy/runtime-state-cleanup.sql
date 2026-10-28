-- Scheduled by the deployment operator, outside CGI requests.
DELETE FROM dbo.t_runtime_state
WHERE expires_at <= SWITCHOFFSET(SYSDATETIMEOFFSET(),'+00:00');
