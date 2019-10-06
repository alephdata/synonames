# Name alias generation

### SQL

```sql
SELECT a, b, COUNT(*) FROM tokens GROUP BY a, b ORDER BY COUNT(*) DESC;

SELECT ARRAY_AGG(a), an, ARRAY_AGG(b), bn, COUNT(*)
    FROM tokens GROUP BY an, bn ORDER BY COUNT(*) DESC LIMIT 999;
```

### Links

* https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-synonym-tokenfilter.html
* https://gist.github.com/dchaplinsky/ad68e3d0887db44766a459c806dbd9d7
