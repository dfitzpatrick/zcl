import { Checkbox, Divider, FormControl, FormControlLabel, FormGroup, MenuItem, Select } from '@material-ui/core'
import { ResponsiveLine } from '@nivo/line'
import moment from 'moment'
import React from 'react'
import { ITimeSeriesObject } from '../../../api/charts'

interface IPlayerIdentifier {
  id: string,
  name: string
  display: boolean,
}

function formatLineData(data: ITimeSeriesObject[], propertyName: string, playerState: IPlayerIdentifier[]) {
  var players: any = {}
  var result = []
  const showPlayers = playerState.filter(v=>v.display).map(v=>v.id)
  //Use profile as a  key in case there are duplicate player names. 
  for (const p of data) {
    if (!showPlayers.includes(p.id)) { continue }
    let game_time = moment.utc(parseFloat(p.game_time) * 1000).format('HH:mm:ss');
    if (!players.hasOwnProperty(p.id)) {
      // No name yet. Add data column
      players[p.id] = { name: p.name, data: [] }
    }
    players[p.id].data.push({
      x: game_time,
      y: p[propertyName]
    })
  }
  for (const p in players) {
    result.push({ id: players[p].name, data: players[p].data })
  }
  return result
}
function uniqueIdentities(players: IPlayerIdentifier[]) {
  const container: IPlayerIdentifier[] = []
  const ids: string[] = []
  for (const p of players) {
    if (!ids.includes(p.id)) {
        container.push(p)
        ids.push(p.id)
    }
  }
  return container
}

interface ITimeChartsProps {
  data: ITimeSeriesObject[]
}

export default function TimeCharts(props: ITimeChartsProps) {
  const [timeSeriesData, setTimeSeriesData] = React.useState<ITimeSeriesObject[]>([])
  const [measure, setMeasure] = React.useState('total_score')
  const [players, setPlayers] = React.useState<IPlayerIdentifier[]>([])
  const matchId = '1550757673'
  React.useEffect(() => {
    setTimeSeriesData(props.data)
    const playerIdentities = uniqueIdentities(props.data.map((s, i) => { return { id: s.id, name: s.name, display: true } }))
    setPlayers(playerIdentities.sort((a,b) => a.name < b.name ? -1 : 1))
  
  }, [props.data])

  const MyResponsiveLine = (data: any, title: string) => (
    <ResponsiveLine
      data={data}
      margin={{ top: 50, right: 110, bottom: 100, left: 60 }}
      xScale={{ type: 'point' }}
      yScale={{ type: 'linear', min: 'auto', max: 'auto', stacked: false, reverse: false }}
      axisTop={null}
      axisRight={null}
      theme={{
        axis: {
          ticks: {
            text: {
              fill: "whitesmoke"
            }
          },
          legend: {
            text: {
              fill: "black"
            }
          },

        },
        legends: {
          text: {
            fill: "whitesmoke"
          }
        },
        tooltip: {
          container: { background: "black" }
        }


      }}
      axisBottom={{
        orient: 'bottom',
        tickSize: 5,
        tickPadding: 5,
        tickRotation: -90,
        legend: 'Game Time',
        legendOffset: 70,
        legendPosition: 'middle'
      }}
      axisLeft={{
        orient: 'left',
        tickSize: 5,
        tickPadding: 5,
        tickRotation: 0,
        legend: title,
        legendOffset: -40,
        legendPosition: 'middle'
      }}
      colors={{ scheme: 'nivo' }}
      pointSize={10}
      pointColor={{ theme: 'background' }}
      pointBorderWidth={2}
      pointBorderColor={{ from: 'serieColor' }}
      pointLabel="y"
      pointLabelYOffset={-12}
      useMesh={true}
      legends={[
        {
          anchor: 'bottom-right',
          direction: 'column',
          justify: false,
          translateX: 100,
          translateY: 0,
          itemsSpacing: 0,
          itemDirection: 'left-to-right',
          itemWidth: 80,
          itemHeight: 20,
          itemOpacity: 0.75,
          symbolSize: 12,
          symbolShape: 'circle',
          symbolBorderColor: 'rgba(0, 0, 0, .5)',
          effects: [
            {
              on: 'hover',
              style: {
                itemBackground: 'rgba(0, 0, 0, .03)',
                itemOpacity: 1
              }
            }
          ]
        }
      ]}
    />
  )
  const handlePlayerFilter = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = players.filter(v=>v.id != event.target.value)
    newValue.push({
      id: event.target.value,
      name: event.target.name,
      display: event.target.checked

    })
    setPlayers(newValue.sort((a,b) => a.name < b.name ? -1 : 1))
  }

  return (
    <div>
      <Select
        value={measure}
        onChange={(e) => {
          const v = e.target.value
          if (typeof (v) == 'string') {
            setMeasure(v)
          }
        }}
      >
        <MenuItem value='total_score'>Total Score</MenuItem>
        <MenuItem value='minerals_floated'>Minerals Floated</MenuItem>
        <MenuItem value='bunkers'>Bunkers</MenuItem>
        <MenuItem value='tanks'>Tanks</MenuItem>
        <MenuItem value='depots'>Depots</MenuItem>
        <MenuItem value='nukes'>Nukes</MenuItem>
        <MenuItem value='current_supply'>Army Supply</MenuItem>
      </Select>
      <div style={{display: 'flex'}}>
      <FormControl component="fieldset">
       
        <FormGroup row>
          {players.map(p => {
            return (

              <FormControlLabel
                control={<Checkbox value={p.id} checked={p.display} onChange={handlePlayerFilter} name={p.name} />}
                label={p.name}
              />

            )
          })}
        </FormGroup>
      </FormControl>
      </div>
      <Divider />
      <div style={{ height: '80vh' }}>
        {MyResponsiveLine(formatLineData(timeSeriesData, measure, players), "Score")}
      </div>

    </div>
  )
}
