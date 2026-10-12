-- 1. Сколько всего клиентов и как они распределены по сегментам
SELECT segment, COUNT(*) AS clients
FROM clients
GROUP BY segment
ORDER BY clients DESC;

-- 2. Диалоги по каналам за последние 30 дней
SELECT channel, COUNT(*) AS dialogues
FROM dialogues
WHERE started_at >= NOW() - INTERVAL '30 days'
GROUP BY channel
ORDER BY dialogues DESC;

-- 3. Статус диалогов и их доли
SELECT status,
       COUNT(*) AS cnt,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM dialogues
GROUP BY status
ORDER BY cnt DESC;

-- 4. Средняя длительность диалога (в минутах) по каналам
SELECT channel,
       ROUND(AVG(EXTRACT(EPOCH FROM (ended_at - started_at)) / 60), 1) AS avg_min
FROM dialogues
WHERE ended_at IS NOT NULL
GROUP BY channel
ORDER BY avg_min DESC;

-- 5. Топ-5 клиентов по числу диалогов
SELECT c.client_id, c.name, c.segment, COUNT(d.dialogue_id) AS dialogues
FROM clients c
JOIN dialogues d ON d.client_id = c.client_id
GROUP BY c.client_id, c.name, c.segment
ORDER BY dialogues DESC
LIMIT 5;

-- 6. Клиенты без единого диалога
SELECT c.client_id, c.name
FROM clients c
LEFT JOIN dialogues d ON d.client_id = c.client_id
WHERE d.dialogue_id IS NULL;

-- 7. Первое и последнее сообщение в каждом диалоге
WITH ranked AS (
    SELECT dialogue_id, text, created_at,
           ROW_NUMBER() OVER (PARTITION BY dialogue_id ORDER BY created_at) AS rn_first,
           ROW_NUMBER() OVER (PARTITION BY dialogue_id ORDER BY created_at DESC) AS rn_last
    FROM messages
)
SELECT dialogue_id,
       MAX(text) FILTER (WHERE rn_first = 1) AS first_msg,
       MAX(text) FILTER (WHERE rn_last = 1)  AS last_msg
FROM ranked
GROUP BY dialogue_id
LIMIT 10;

-- 8. Количество сообщений в диалоге: среднее, медиана, максимум
WITH msg_cnt AS (
    SELECT dialogue_id, COUNT(*) AS n
    FROM messages
    GROUP BY dialogue_id
)
SELECT ROUND(AVG(n), 2) AS avg_msgs,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY n) AS median_msgs,
       MAX(n) AS max_msgs
FROM msg_cnt;

-- 9. Динамика по дням: сколько диалогов стартовало каждый день
SELECT DATE(started_at) AS day, COUNT(*) AS dialogues
FROM dialogues
GROUP BY day
ORDER BY day;

-- 10. Клиенты с более одного диалога
SELECT client_id, COUNT(*) AS n
FROM dialogues
GROUP BY client_id
HAVING COUNT(*) > 1
ORDER BY n DESC;
