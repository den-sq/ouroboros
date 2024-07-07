// import OptionsPanel from '@renderer/components/OptionsPanel/OptionsPanel'
import styles from './BackprojectPage.module.css'
import VisualizePanel from '@renderer/components/VisualizePanel/VisualizePanel'
import ProgressPanel from '@renderer/components/ProgressPanel/Progress'
import ServerProvider from '@renderer/contexts/ServerContext/ServerContext'

function BackprojectPage(): JSX.Element {
	return (
		<ServerProvider>
			<div className={styles.backprojectPage}>
				<VisualizePanel />
				<ProgressPanel />
				{/* <OptionsPanel /> */}
			</div>
		</ServerProvider>
	)
}

export default BackprojectPage
