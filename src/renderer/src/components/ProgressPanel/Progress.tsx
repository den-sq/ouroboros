import Header from '../Header/Header'
import ProgressBar from './components/ProgressBar/ProgressBar'
import ServerConnectedIndicator from './components/ServerConnectedIndicator/ServerConnectedIndicator'

function ProgressPanel(): JSX.Element {
	return (
		<div className="panel">
			<Header text={'Progress'} />
			<ServerConnectedIndicator connected={false} />
			<ProgressBar progress={100} name={'Loading'} />
			<ProgressBar progress={25} name={'Loading'} />
			<ProgressBar progress={10} name={'Loading'} />
			<ProgressBar progress={0} name={'Loading'} />
		</div>
	)
}

export default ProgressPanel
