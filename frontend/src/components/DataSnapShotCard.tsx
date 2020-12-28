import { Button, Card, CardActions, CardContent, CardHeader, CardMedia, Divider, Grid, makeStyles, Typography } from '@material-ui/core'
import React from 'react'

interface CardDataItem {
  title: string,
  data: string
}

interface IDataSnapshotCardProps {
  maxWidth?: number
  dataItems?: CardDataItem[]
}
const useStyles = makeStyles({
  root: {
    justifyContent: 'space-between'
  },
  item: {
    margin: '5px'

  }

})
const sampleData = [
  {
    title: "Games Played",
    data: "10"
  },
  {
    title: "Games Won",
    data: "8"
  }
]
export default function DataSnapshotCard(props: IDataSnapshotCardProps) {
  const classes = useStyles()
  const dataItems = props.dataItems ?? sampleData
  const renderDivider = (idx: number, length: number) => {
    if (idx + 1 < length) {
      return (
        <Grid item className={classes.item}>
          <Divider orientation="vertical"></Divider>
        </Grid>
      )
    }
  }

  return (
    <div>
      <Card style={{ maxWidth: props.maxWidth ?? 500 }}>
        <CardContent>
          <Grid container>
            {dataItems.map((o, idx, parent) => {
              const divider = renderDivider(idx, parent.length)
              return (
                <>
                  <Grid item className={classes.item}>
                    <Typography variant="h5" component="h2">{o.title ?? "Games Today"}</Typography>
                    <Typography color="textPrimary" variant="h1" component="h1">{o.data}</Typography>
                  
                  </Grid>
                  {divider}

                </>

              )
            })}

          </Grid>

        </CardContent>
        <CardActions>
          <Button variant="outlined" color="secondary">Test</Button>
        </CardActions>
      </Card>



    </div>
  )
}

