def allocate_to_yuu(user_spending, min_spend=600, cap=600, bonus_cats=['dining', 'groceries', 'transport']):

    # 1. Allocate as much bonus spend as possible up to cap
    yuu_spending = {}
    bonus_spent = 0
    for cat in bonus_cats:
        amt = min(user_spending.get(cat, 0), cap - bonus_spent)
        if amt > 0:
            yuu_spending[cat] = amt
            bonus_spent += amt
        if bonus_spent >= cap:
            break

    # 2. If bonus < min_spend, top up with non-bonus
    total_yuu = sum(yuu_spending.values())
    if total_yuu < min_spend:
        needed = min_spend - total_yuu
        for cat, amt in user_spending.items():
            if cat not in bonus_cats and needed > 0:
                alloc = min(amt, needed)
                if alloc > 0:
                    yuu_spending[cat] = yuu_spending.get(cat, 0) + alloc
                    needed -= alloc

    # 3. Allocate remaining spend to other cards
    other_spending = {}
    for cat, amt in user_spending.items():
        yuu_amt = yuu_spending.get(cat, 0)
        other_amt = amt - yuu_amt
        if other_amt > 0:
            other_spending[cat] = other_amt
    return yuu_spending, other_spending
