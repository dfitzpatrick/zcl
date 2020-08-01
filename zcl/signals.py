from django.dispatch import Signal

# ZCL Related Signals

"""
Match Foreign keys won't update through post_save. Since there could be any
number of rosters it is hard to predict. Using this as a custom signal when
we know that the match has all relations
"""

new_match = Signal(providing_args=['instance'])