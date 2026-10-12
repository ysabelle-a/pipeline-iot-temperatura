
-- View 1: resumo diario das temperaturas
CREATE OR REPLACE VIEW vw_temperatura_diaria AS
SELECT
    DATE(reading_time) AS dia,
    COUNT(*) AS total_leituras,
    ROUND(AVG(temperature)::numeric, 2) AS temperatura_media
FROM temperature_readings
GROUP BY DATE(reading_time);


-- View 2: resumo diario separado por localizacao
CREATE OR REPLACE VIEW vw_temperatura_diaria_localizacao AS
SELECT
    DATE(reading_time) AS dia,
    location_type,
    COUNT(*) AS total_leituras,
    ROUND(AVG(temperature)::numeric, 2) AS temperatura_media
FROM temperature_readings
GROUP BY DATE(reading_time), location_type;


-- View 3: quantidade de leituras por faixa de temperatura
CREATE OR REPLACE VIEW vw_classificacao_temperatura AS
SELECT
    CASE
        WHEN temperature < 25 THEN 'Baixa'
        WHEN temperature < 35 THEN 'Moderada'
        ELSE 'Alta'
    END AS faixa_temperatura,
    COUNT(*) AS total_leituras
FROM temperature_readings
GROUP BY
    CASE
        WHEN temperature < 25 THEN 'Baixa'
        WHEN temperature < 35 THEN 'Moderada'
        ELSE 'Alta'
    END;
