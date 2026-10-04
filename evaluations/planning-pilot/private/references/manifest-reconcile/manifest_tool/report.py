def totals(before,after):
    old=sum(x['size'] for x in before);new=sum(x['size'] for x in after)
    return {'before_bytes':old,'after_bytes':new,'delta_bytes':new-old}
