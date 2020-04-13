/*!

=========================================================
* Material Dashboard PRO React - v1.8.0
=========================================================

* Product Page: https://www.creative-tim.com/product/material-dashboard-pro-react
* Copyright 2019 Creative Tim (https://www.creative-tim.com)

* Coded by Creative Tim

=========================================================

* The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

*/
import React from "react";
import ReactDOM from "react-dom";
import { createBrowserHistory } from "history";
import { Router, Route, Switch, Redirect } from "react-router-dom";

import AuthLayout from "layouts/Auth.js";
import RtlLayout from "layouts/RTL.js";
import AdminLayout from "layouts/Admin.js";
import { withStore, useStore} from 'react-context-hook'
import "assets/scss/material-dashboard-pro-react.scss?v=1.8.0";
import {userInitialState} from "variables/general.js"
import axios from "axios";
const hist = createBrowserHistory();

async function getCurrentUser() {
  // Relies on session state from login
  const response = await axios.get('/api/current_user')
  return response.data
}


export const PrivateRoute = ({ component: Component, ...rest }) => {
  const [user, setUser, deleteUser] = useStore('user', userInitialState)
  console.log(user.authorized)
  if (user.loading) {
    return (<div>Loading!</div>)
  }
  if (!user.authorized) {
    getCurrentUser().then(user => {
      setUser({loading: false, token: user.token, authorized: user.authorized, user: user.details})
    })
  }
  return (
  <Route {...rest} render={(props) => (
    user.authorized === true
      ? <Component {...props} />
      : <Redirect to='/' />
  )} />
  )
}

export default function App() {
  const [user, setUser, deleteUser] = useStore('user', userInitialState)
  React.useEffect(() => {
    getCurrentUser().then(user => {
      setUser({loading: false, token: user.token, authorized: user.authorized, user: user.details})
    })
  }, [])
  return (
    <div>
      <Router history={hist}>
      <Switch>
      <Route exact path="/" component={AuthLayout} />
      <PrivateRoute path="/portal" component={AdminLayout} />
      <PrivateRoute path="/portal/matches/:id" component={AdminLayout} />
      
    </Switch>
    </Router>
    </div>
  )
}
//Don't want to use anything crazy like redux. Simply need the user and thats about it.
const StoreApp = withStore(App, userInitialState)

ReactDOM.render(
  <StoreApp />,
  document.getElementById("root")
);
