import React from 'react'
import { Redirect, Route, RouteProps } from 'react-router'
import { UserContext } from '../UserProvider/UserProvider'
export interface IPrivateRouteProps extends RouteProps {
    //Nothing yet
}
const PrivateRoute: React.FC<IPrivateRouteProps> = (props) => {
    const user = React.useContext(UserContext)
    console.log('private route user is ')
    console.log(user)
   return user != undefined ? (
    <Route {...props} component={props.component} render={undefined} />
  ) : (
    <Redirect push to='/accounts/login' />
  )
}

export default PrivateRoute