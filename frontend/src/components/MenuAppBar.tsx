import { Avatar, Button } from '@material-ui/core';
import AppBar from '@material-ui/core/AppBar';
import IconButton from '@material-ui/core/IconButton';
import Menu from '@material-ui/core/Menu';
import MenuItem from '@material-ui/core/MenuItem';
import { createStyles, makeStyles, Theme } from '@material-ui/core/styles';
import Toolbar from '@material-ui/core/Toolbar';
import Typography from '@material-ui/core/Typography';
import React from 'react';
import { Link } from 'react-router-dom';
import { UserContext } from './UserProvider/UserProvider';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      flexGrow: 1,
    },
    menuButton: {
      marginRight: theme.spacing(2),
      flexGrow: 1,
    },
    title: {
      flexGrow: 1,
    },
    links: {
      flexGrow: 1,
    }


  }),
)
export default function MenuAppBar() {
  const user = React.useContext(UserContext)
  const classes = useStyles();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);



  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };
  const handleAccount = () => {
    window.location.href = '/account'
  };
  const handleLogin = () => {
    window.location.href = '/accounts/login'
  }
  const handleLogout = () => {
    window.location.href = '/accounts/logout'
  }
  const authButton = () => {
    if (user) {
      return (
        <div>
          <IconButton
            aria-label="account of current user"
            aria-controls="menu-appbar"
            aria-haspopup="true"
            onClick={handleMenu}
            color="inherit"
          >
            <Avatar src={`https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png`} />
          </IconButton>
          <Menu
            id="menu-appbar"
            anchorEl={anchorEl}
            anchorOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            keepMounted
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            open={open}
            onClose={handleClose}
          >
            <MenuItem onClick={handleAccount}>Account</MenuItem>
            <MenuItem onClick={handleLogout}>Log out</MenuItem>
          </Menu>
        </div>
      )
    } else {
      return (
        <Button onClick={handleLogin}>Login</Button>

      )
    }
  }
  return (
    <div className={classes.root}>
      <AppBar position="static">
        <Toolbar>
          <Link to='/'>
            <Button>
              <Typography variant="h6" className={classes.title}>
                ZCLEAGUES
            </Typography>
            </Button>
          </Link>

          <div className={classes.links}>
            <Link to='/leaderboard'>
              <Button className={classes.menuButton}>Leaderboard </Button></Link>
            <Link to='/matches'>
              <Button className={classes.menuButton}>Matches</Button>
            </Link>
            <Link to='/leagues'>
              <Button className={classes.menuButton}>Leagues</Button>
            </Link>
          </div>
          
          {authButton()}
         
        </Toolbar>
      </AppBar>
    </div>
  );
}
