        CREATE OR REPLACE FUNCTION user_role_assignments(query_uuid UUID)
        RETURNS TABLE (
            uuid UUID,
            created_at TIMESTAMP WITH TIME ZONE,
            updated_at TIMESTAMP WITH TIME ZONE,
            assignee_uuid UUID,
            entity_uuid UUID,
            status TEXT,
            domain_uuid UUID,
            assignee_type TEXT,
            entity_type TEXT,
            role_uuid UUID
        ) AS $$        
        BEGIN
            RETURN QUERY
            WITH
                user_organization_units AS (
                    SELECT organization_unit_uuid AS uuid
                    FROM organization_unit_user_links
                    WHERE user_uuid = query_uuid
                ),               
                all_user_organization_units AS (
                    WITH RECURSIVE children AS (
                        SELECT organization_units.uuid, organization_units.parent_organization_unit_uuid
                        FROM organization_units 
                        WHERE organization_units.uuid IN (SELECT user_organization_units.uuid FROM user_organization_units)

                        UNION ALL
                        
                        SELECT ou.uuid, ou.parent_organization_unit_uuid
                        FROM organization_units ou
                        JOIN children c ON ou.parent_organization_unit_uuid = c.uuid
                    )
                    SELECT children.uuid FROM children
                ),
                organization_member AS (
                    SELECT organization_uuid AS uuid
                    FROM users
                    WHERE users.uuid = query_uuid
                ),
                organization_member_organization_units AS (
                    SELECT organization_units.uuid AS uuid
                    FROM organization_units
                    JOIN organization_member
                        ON (
                            organization_units.organization_uuid = organization_member.uuid
                        )
                ),
                organization_owner AS (
                    SELECT role_assignments.entity_uuid AS uuid
                    FROM role_assignments
                    WHERE
                        role_assignments.entity_type = 'ORGANIZATION' AND
                        role_assignments.assignee_type = 'USER' AND
                        role_assignments.assignee_uuid = query_uuid
                ),
                organization_owner_organization_units AS (
                    SELECT organization_units.uuid AS uuid
                    FROM organization_units
                    JOIN organization_owner
                        ON (
                            organization_units.organization_uuid = organization_owner.uuid
                        )
                )

            SELECT DISTINCT
                role_assignments.uuid,
                role_assignments.created_at::TIMESTAMP WITH TIME ZONE,
                role_assignments.updated_at::TIMESTAMP WITH TIME ZONE,
                role_assignments.assignee_uuid,
                role_assignments.entity_uuid,
                role_assignments.status::TEXT,
                role_assignments.domain_uuid,
                role_assignments.assignee_type::TEXT,
                role_assignments.entity_type::TEXT,
                role_assignments.role_uuid
            FROM
                role_assignments
                LEFT JOIN organization_units
                    ON (
                        organization_units.uuid = role_assignments.assignee_uuid AND
                        role_assignments.assignee_type = 'ORGANIZATION_UNIT'
                    )
                LEFT JOIN organizations
                    ON (
                        organizations.uuid = role_assignments.assignee_uuid AND
                        role_assignments.assignee_type = 'ORGANIZATION' OR
                        organizations.uuid = role_assignments.entity_uuid AND
                        role_assignments.entity_type = 'ORGANIZATION'
                    )
            WHERE role_assignments.assignee_uuid = query_uuid AND role_assignments.assignee_type = 'USER'
                OR organization_units.uuid IN (SELECT all_user_organization_units.uuid FROM all_user_organization_units)
                OR (
                    organizations.uuid IN (SELECT organization_member.uuid FROM organization_member) AND
                    role_assignments.assignee_type = 'ORGANIZATION'
                )
                OR organization_units.uuid IN (SELECT organization_member_organization_units.uuid FROM organization_member_organization_units)
                OR organizations.uuid IN (SELECT organization_owner.uuid FROM organization_owner)
                OR organization_units.uuid IN (SELECT organization_owner_organization_units.uuid FROM organization_owner_organization_units);
        END;
