
import React from 'react'
import {Theme, makeStyles, createStyles } from '@material-ui/core'

const useStyles = makeStyles((theme: Theme) => createStyles({
    root: {
      marginTop: '2em',
    },
}))

export default function MarginContainer(props: React.PropsWithChildren<{}>) {
    const classes = useStyles()
    return (
        <div className={classes.root}>
            {props.children}
        </div>
    )
}
