import React from 'react'
import { ResponsiveLine } from '@nivo/line'
import moment from 'moment'
import Select from '@material-ui/core/Select';
import MenuItem from '@material-ui/core/MenuItem';
// make sure parent container have a defined height when using
// responsive component, otherwise height will be 0 and
// no chart will be rendered.
// website examples showcase many properties,
// you'll often use just a few of them.

function compare(a, b) {
    let at = parseFloat(a.x)
    let bt = parseFloat(b.y)
    if (at > bt) return -1
    if (bt > at) return 1
    return 0
}
function formatLineData(data, propertyName) {
    var players = {}
    var result = []
    //Use profile as a  key in case there are duplicate player names. 
    for (const p of data) {
        let game_time = moment.utc(p.game_time*1000).format('HH:mm:ss');
        //let game_time = parseFloat(p.game_time)
        if (!players.hasOwnProperty(p.id)) {
            // No name yet. Add data column
            players[p.id] = {name: p.name, data: []} 
        }
        players[p.id].data.push({
            x: game_time,
            y: p[propertyName]
        })
    }
    for (const p in players) {
        result.push({id: players[p].name, data: players[p].data})
    }
    return result
}

const MyResponsiveLine = (data, title) => (
    <ResponsiveLine
        data={data}
        margin={{ top: 50, right: 110, bottom: 100, left: 60 }}
        xScale={{ type: 'point' }}
        yScale={{ type: 'linear', min: 'auto', max: 'auto', stacked: false, reverse: false }}
        axisTop={null}
        axisRight={null}
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


export default function StatsTrend(props) {
    //let data = foxData2
    let data = props.data == undefined ? [] : props.data

    let title = props.title == undefined ? "Score" : props.title
    const [selection, setSelection] = React.useState("total_score")

    const handleChange = (event) => {
        setSelection(event.target.value);
      }
    return (
        <>
        <div>
        <Select
          labelId="demo-simple-select-label"
          id="demo-simple-select"
          value={selection}
          onChange={handleChange}
        >
          <MenuItem value='total_score'>Total Score</MenuItem>
          <MenuItem value='minerals_floated'>Minerals Floated</MenuItem>
          <MenuItem value='bunkers'>Bunkers</MenuItem>
          <MenuItem value='tanks'>Tanks</MenuItem>
          <MenuItem value='depots'>Depots</MenuItem>
          <MenuItem value='nukes'>Nukes</MenuItem>
          <MenuItem value='current_supply'>Army Supply</MenuItem>

        </Select>
        </div>
        <div style={{height: '800px'}}>
            {MyResponsiveLine(formatLineData(data, selection), title)}
        </div>
        </>
    )
}
