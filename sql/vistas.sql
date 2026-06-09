-- 1. Vista de Solicitudes Pendientes
CREATE OR REPLACE VIEW vista_solicitudes_pendientes AS
SELECT
    a.id_amistad,
    a.fecha_amistad,
    us.nombre AS usuario_solicitante,
    ur.nombre AS usuario_receptor
FROM amistades a
JOIN usuarios us ON a.usuario_solicitante_id = us.id_usuario
JOIN usuarios ur ON a.usuario_receptor_id = ur.id_usuario
WHERE a.estado = 'PENDIENTE';

-- 2. Vista de Amistades Consolidadas (Aceptadas)
CREATE OR REPLACE VIEW vista_amistades_consolidadas AS
SELECT
    a.id_amistad,
    a.fecha_amistad,
    us.nombre AS usuario_1,
    ur.nombre AS usuario_2
FROM amistades a
JOIN usuarios us ON a.usuario_solicitante_id = us.id_usuario
JOIN usuarios ur ON a.usuario_receptor_id = ur.id_usuario
WHERE a.estado = 'ACEPTADA';

-- 3. Vista Feed de Noticias (con COUNT de comentarios)
CREATE OR REPLACE VIEW vista_feed_noticias AS
SELECT
    p.id_publicacion,
    u.nombre AS autor_publicacion,
    p.texto_contenido,
    p.fecha_publicacion,
    p.likes_contador,
    COUNT(c.id_comentario) AS total_comentarios
FROM publicaciones p
JOIN usuarios u ON p.autor_id = u.id_usuario
-- Usamos LEFT JOIN por si una publicación no tiene comentarios aún
LEFT JOIN comentarios c ON p.id_publicacion = c.publicacion_id
GROUP BY
    p.id_publicacion,
    u.nombre,
    p.texto_contenido,
    p.fecha_publicacion,
    p.likes_contador;