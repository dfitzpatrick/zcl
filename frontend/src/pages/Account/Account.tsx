
import { Tab } from '@material-ui/core'
import { TabContext, TabList, TabPanel } from '@material-ui/lab'
import React from 'react'
import MarginContainer from '../../components/MarginContainer/MarginContainer'
import { parseSimpleQuerystring } from '../../helpers'
import AccountBanner from './components/AccountBanner'
import AccountProfiles from './components/AccountProfiles'
import AccountTwitchConnections from './components/AccountTwitchConnections'

export default function Account() {
    const { tabId } = parseSimpleQuerystring(window.location.search)
    const [tabValue, setTabValue] = React.useState(tabId ?? "profiles")
    return (
        <MarginContainer>
            <AccountBanner />
            <TabContext value={tabValue}>
              <TabList onChange={(e, v) => setTabValue(v)}>
                <Tab label="Profiles" value="profiles" />
                <Tab label="Twitch Connections" value="twitchConnections" />
         
              </TabList>
             
              <TabPanel value="profiles">
                <AccountProfiles />
              </TabPanel>

              <TabPanel value="twitchConnections">
                <AccountTwitchConnections />
              </TabPanel>

              </TabContext>
        </MarginContainer>
    )
}
