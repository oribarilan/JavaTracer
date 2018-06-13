select count(*) as trace_count, tmid
from traces
group by traces.tmid
order by trace_count desc