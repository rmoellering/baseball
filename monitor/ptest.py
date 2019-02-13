from utils import get_duration

ends = (
	'2018-11-20 00:00:01',
	'2018-11-20 00:01:00',
	'2018-11-20 00:02:02',
	'2018-11-20 03:00:04',
	'2018-11-20 03:04:05',
	'2018-11-21 00:00:00',
	'2018-11-22 16:00:00',
	'2018-11-23 00:56:00',
	'2018-11-27 00:14:45',
	'2018-12-30 12:34:56',
)

for end in ends:
	print(
		get_duration(
			start='2018-11-20 00:00:00',
			end=end
		)
	)
