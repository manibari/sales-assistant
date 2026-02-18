-- database/queries/crm_get_all.sql
-- Retrieves all CRM clients, joining with contacts to get DM and Champion names.

SELECT c.*,
       dm_contact.name AS dm_name,
       champ_agg.champion_names
FROM crm c
LEFT JOIN (
    SELECT ac.client_id, ct.name
    FROM account_contact ac
    JOIN contact ct ON ac.contact_id = ct.contact_id
    WHERE ac.role = 'decision_maker'
) dm_contact ON c.client_id = dm_contact.client_id
LEFT JOIN (
    SELECT ac.client_id,
           STRING_AGG(ct.name, ', ' ORDER BY ac.sort_order) AS champion_names
    FROM account_contact ac
    JOIN contact ct ON ac.contact_id = ct.contact_id
    WHERE ac.role = 'champion'
    GROUP BY ac.client_id
) champ_agg ON c.client_id = champ_agg.client_id
ORDER BY c.client_id;
