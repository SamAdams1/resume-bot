USE apply_jobs;
SELECT * FROM jobs;
SELECT title, company, url FROM jobs;
SELECT title, reason, url, query FROM excluded_jobs;

DROP TABLE jobs;
DROP TABLE excluded_jobs;