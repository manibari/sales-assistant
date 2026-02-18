-- database/queries/project_get_closed.sql
-- Retrieves projects in closed states (P2, LOST, HOLD), joining with CRM
-- data to get client company information.

SELECT p.*, c.company_name, c.department,
       c.decision_maker, c.champions, c.industry
FROM project_list p
LEFT JOIN crm c ON p.client_id = c.client_id
WHERE p.status_code = ANY(%s)
ORDER BY c.company_name, p.project_id;
