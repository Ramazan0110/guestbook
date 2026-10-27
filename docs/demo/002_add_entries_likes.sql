-- Обратно совместимая миграция (expand): только добавляем колонку с DEFAULT.
-- Старая версия приложения её не знает и не читает: её INSERT и SELECT продолжают работать,
-- поэтому откат кода на предыдущий тег безопасен, а данные остаются на месте.
ALTER TABLE entries ADD COLUMN IF NOT EXISTS likes integer NOT NULL DEFAULT 0;
