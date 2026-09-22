TCP notes (lecture 4)

tcp = transmission control protocol. it's reliable, udp is not. basically tcp makes sure
packets arrive + in order. uses a 3 way handshake before sending data: SYN, SYN-ACK, ACK

sequence numbers - each byte gets a number?? not sure if per byte or per packet. check this

if a packet is lost the sender resends after timeout. there is also something called fast
retransmit when you get 3 duplicate acks

flow control vs congestion control -- flow control = receiver says how much it can take
(window size). congestion control = ... something about slow start, window doubles every RTT

tcp is always slower than udp
