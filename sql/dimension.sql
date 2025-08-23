-- Dimension: Browsers
CREATE TABLE IF NOT EXISTS clickstream.dim_browser (
    id INT PRIMARY KEY,
    name TEXT
);

-- Dimension: Operating Systems
CREATE TABLE IF NOT EXISTS clickstream.dim_os (
    id INT PRIMARY KEY,
    name TEXT
);

-- Dimension: Regions
CREATE TABLE IF NOT EXISTS clickstream.dim_region (
    id INT PRIMARY KEY,
    name TEXT
);

-- Dimension: Traffic Types
CREATE TABLE IF NOT EXISTS clickstream.dim_traffic (
    id INT PRIMARY KEY,
    name TEXT
);
INSERT INTO clickstream.dim_browser (id, name) VALUES
(1,'Browser 1'),(2,'Browser 2'),(3,'Browser 3'),(4,'Browser 4'),
(5,'Browser 5'),(6,'Browser 6'),(7,'Browser 7'),(8,'Browser 8'),
(9,'Browser 9'),(10,'Browser 10'),(11,'Browser 11'),(12,'Browser 12'),
(13,'Browser 13')
ON CONFLICT (id) DO NOTHING;

INSERT INTO clickstream.dim_os (id, name) VALUES
(1,'OS 1'),(2,'OS 2'),(3,'OS 3'),(4,'OS 4'),
(5,'OS 5'),(6,'OS 6'),(7,'OS 7'),(8,'OS 8')
ON CONFLICT (id) DO NOTHING;

INSERT INTO clickstream.dim_region (id, name) VALUES
(1,'Region 1'),(2,'Region 2'),(3,'Region 3'),(4,'Region 4'),
(5,'Region 5'),(6,'Region 6'),(7,'Region 7'),(8,'Region 8'),(9,'Region 9')
ON CONFLICT (id) DO NOTHING;

INSERT INTO clickstream.dim_traffic (id, name) VALUES
(1,'Traffic 1'),(2,'Traffic 2'),(3,'Traffic 3'),(4,'Traffic 4'),
(5,'Traffic 5'),(6,'Traffic 6'),(7,'Traffic 7'),(8,'Traffic 8'),
(9,'Traffic 9'),(10,'Traffic 10'),(11,'Traffic 11'),(12,'Traffic 12'),
(13,'Traffic 13'),(14,'Traffic 14'),(15,'Traffic 15'),(16,'Traffic 16'),
(17,'Traffic 17'),(18,'Traffic 18'),(19,'Traffic 19'),(20,'Traffic 20')
ON CONFLICT (id) DO NOTHING;
