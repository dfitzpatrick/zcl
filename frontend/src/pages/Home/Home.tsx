import { Button, createStyles, Grid, makeStyles, Paper, Theme, Typography } from '@material-ui/core'
import React from 'react'
import MarineBG from '../../assets/img/marine.jpg'
import Leaderboard from '../../components/Leaderboard/Leaderboard'
import './Home.css'

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    backgroundImage: `url(${MarineBG})`,
    display: 'flex',
    justifyContent: 'space-between',
    verticalAlign: 'center',
    backgroundPosition: 'center',
    height: '100vh',
    width: '100%',

    backgroundSize: 'cover',
    backgroundRepeat: 'no-repeat'

  },
  title: {
    display: 'flex'
  },
  paper: {
    padding: theme.spacing(2),
    textAlign: 'center',
    color: theme.palette.text.primary,
  },
  statsContainer: {
    backgroundColor: theme.palette.text.primary,
    width: '100%',
    height: '100vh',
    opacity: 1,
    justifyContent: 'center',
    alignItems: 'center',
  }
}))
export default function Home() {
  const classes = useStyles()
  return (
    <div className='splash-container'>
      <Grid container spacing={2} className="grid-container">
        <Grid item xs={12} className='splash-title'>
          <Paper className={classes.paper}>
            <Typography variant="h1">ZC LEAGUES</Typography>
            <Typography variant="h5" color="secondary">
              A Zone Control: CE Community dedicated to pre-arranged games and statistical tracking.
                       </Typography>
            <Button style={{ margin: '2em' }} variant="contained"
              onClick={(e) => window.location.href = 'https://discord.gg/7xr5sZq'}
            >Join the Discord</Button>
          </Paper>
        </Grid>

        <Grid item xs={12} className='splash-lobbies'>
          <Paper className={classes.paper}>
            <Leaderboard
              title="Leaderboard Top 5"
              noFilter
              filters={{
                limit: 5,
                offset: 0,
                mode: '2v2v2v2'
              }}
              options={{
                pageSize: 5,
                toolbar: false,
                sorting: false,
                paging: false,
              }}
            />
          </Paper>
        </Grid>





      </Grid>

    </div>
  )
}
