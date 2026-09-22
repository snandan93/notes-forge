DNS

dns turns names like google.com into IP addresses. your computer asks a resolver
(usually your ISP or 8.8.8.8) and it goes root server -> .com server -> google's server

TTL = how long the answer is cached. lower TTL = faster updates but more queries?

A record = ipv4, AAAA = ipv6, CNAME = alias. MX for email

dns uses UDP only (port 53)
