# define parameters
USER='yint'
PI='rasp-008.berry.scss.tcd.ie'
JUMPER='macneill.scss.tcd.ie'

# run remote classification
ssh -J $USER@$JUMPER $USER@$PI "cd ~/Jerry-Net/Jerry-Net; bash pi_shell.sh"


