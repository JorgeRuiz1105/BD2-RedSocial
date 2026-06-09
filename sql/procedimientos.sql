CREATE OR REPLACE PROCEDURE crear_amistad(id_usuario1 INT, id_usuario2 INT)
LANGUAGE plpgsql
AS $$
DECLARE
    nuevo_id INT;
BEGIN
    -- 1. Validamos si la amistad ya existe en cualquier dirección
    IF EXISTS (
        SELECT 1 FROM amistades
        WHERE (usuario_solicitante_id = id_usuario1 AND usuario_receptor_id = id_usuario2)
           OR (usuario_solicitante_id = id_usuario2 AND usuario_receptor_id = id_usuario1)
    ) THEN
        RAISE EXCEPTION 'Oye, ¡esta solicitud de amistad ya existe o ya son amigos!';
    END IF;

    -- 2. Calculamos el siguiente ID disponible manualmente
    SELECT COALESCE(MAX(id_amistad), 0) + 1 INTO nuevo_id FROM amistades;

    -- 3. Insertamos incluyendo el ID calculado y la fecha actual
    INSERT INTO amistades (id_amistad, fecha_amistad, usuario_solicitante_id, usuario_receptor_id, estado)
    VALUES (nuevo_id, CURRENT_DATE, id_usuario1, id_usuario2, 'PENDIENTE');
END;
$$;