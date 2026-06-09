CREATE OR REPLACE PROCEDURE crear_amistad(id_usuario1 INT, id_usuario2 INT)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Validamos si la amistad ya existe en cualquier dirección
    IF EXISTS (
        SELECT 1 FROM amistades
        WHERE (usuario_solicitante_id = id_usuario1 AND usuario_receptor_id = id_usuario2)
           OR (usuario_solicitante_id = id_usuario2 AND usuario_receptor_id = id_usuario1)
    ) THEN
        RAISE EXCEPTION 'Oye, ¡esta solicitud de amistad ya existe o ya son amigos!';
    END IF;

    -- Si pasa la validación, insertamos la relación como PENDIENTE
    INSERT INTO amistades (usuario_solicitante_id, usuario_receptor_id, estado)
    VALUES (id_usuario1, id_usuario2, 'PENDIENTE');
END;
$$;