# define parameters
USER=<your_user_name>
PI=<your_pi_address>
SRC='Jerry-Net'
DST='~/Jerry-Net'
MODEL='models'
JUMPER='macneill.scss.tcd.ie'

# run deployment
# make a new folder for everythin
rm -r $SRC
mkdir -p $SRC
cp -r main $SRC
cp requirements.txt $SRC
cp pi_shell.sh $SRC

# push the folder to remote
#clean
ssh -J $USER@$JUMPER $USER@$PI "rm -rf $DST"
#scp
scp -rp -J $USER@$JUMPER $SRC $USER@$PI:$DST

if [ $? == 0 ]; then
  echo '----deployment successful----'
else
  echo '----fail to upload files----'
  exit 1
fi