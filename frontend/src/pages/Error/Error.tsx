import { createStyles, makeStyles, Theme, Typography } from '@material-ui/core'
import React from 'react'
import Nova from '../../assets/img/nova.jpg'
import {parseSimpleQuerystring } from '../../helpers'

const useStyles = makeStyles((theme: Theme) => createStyles({
    container: {
        backgroundImage: `linear-gradient( rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5) ),  url(${Nova})`,
        backgroundSize: 'cover',
        backgroundRepeat: 'no-repeat',
        display: 'flex',
        flexDirection: 'column',
    justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
    
    },
    item: {
        textAlign: 'center'
    }
    
  }))
export default function Error() {
    const classes = useStyles()
    const { msg } = parseSimpleQuerystring(window.location.search)
    return (
        <div className={classes.container}>
            <div className={classes.item}>
                <Typography variant="h1">Oops (EZ)</Typography>
            </div>
            <div className={classes.item}>
                <Typography variant="h4">{msg}</Typography>
            </div>
        </div>
    )
}
