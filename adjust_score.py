def main(u_id, adj, r):

    score_key = 'Score_%s'%(u_id)
    r.incr(score_key, adj)
