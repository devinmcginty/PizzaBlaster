from datetime import timedelta

def timeToSecs(time):
    score_times = time.split(":")
    score_times.reverse()

    seconds = minutes = hours = days = 0

    if len(score_times) > 0:
        seconds = int(score_times[0])
    if len(score_times) > 1:
        minutes = int(score_times[1])
    if len(score_times) > 2:
        hours = int(score_times[2])
    if len(score_times) > 3:
        days = int(score_times[3])

    score_delta = timedelta(
        seconds=seconds,
        minutes=minutes,
        hours=hours,
        days=days
    )

    score_seconds = score_delta.total_seconds()

    return score_seconds
