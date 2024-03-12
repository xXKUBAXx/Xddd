git pull origin master
git submodule init
git submodule update
source ../env/bin/activate
python3 manage.py migrate
python3 manage.py collectstatic --noinput