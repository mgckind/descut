#INSERT INTO Jobs VALUES(?, ?, ?, ?, ?, ?, ?, ?)
#        Jobs(user text, job text, status text, time datetime, type text, query mediumtext, files text, sizes text)")
#'83bc4dc1-69c4-42d4-bab0-bd533338a3bb'
import random
import string
import datetime
import sys

#''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
#print jobid
def easy_job(user, status, num, filename):
	for i in range(0, num):
		job = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8)) + '-' + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4)) + '-' + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4)) + '-' + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4)) + '-' + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(12)) 
		time = datetime.datetime.now()
		print "INSERT INTO Jobs VALUES('{usern}', '{jobid}', '{status}', '{time}', '{type}', '{query}', '{files}', '{size}');".format(usern = user, jobid = job, status = status, time = time, type = 'EASY', query = 'select 3 from dual', files = filename, size = '') 	

def des_job(user, status, num):
	for i in range(0, num):
                #job = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
                job = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8)) + '-' + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4)) + '-' + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4)) + '-' + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4)) + '-' + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(12))

		time = datetime.datetime.now()
                print "INSERT INTO Jobs VALUES('{usern}', '{jobid}', '{status}', '{time}', '{type}', '{query}', '{files}', '{size}');".format(usern = user, jobid = job, status = status, time = time, type = 'DES', query = '', files = '', size = '')

def main():
	user = sys.argv[2]
	status = sys.argv[3].upper()
	num = int(sys.argv[4])
	filename = sys.argv[5]
	if sys.argv[1] == "easy":
		easy_job(user, status, num, filename)
	else:
		des_job(user, status, num)
		
if __name__ == "__main__":
	main()

