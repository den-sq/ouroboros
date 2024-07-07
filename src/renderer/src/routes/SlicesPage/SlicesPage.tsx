import OptionsPanel from '@renderer/components/OptionsPanel/OptionsPanel'
import styles from './SlicesPage.module.css'
import VisualizePanel from '@renderer/components/VisualizePanel/VisualizePanel'
import ProgressPanel from '@renderer/components/ProgressPanel/Progress'
import ServerProvider from '@renderer/contexts/ServerContext/ServerContext'

function SlicesPage(): JSX.Element {
	return (
		<ServerProvider>
			<div className={styles.slicePage}>
				<VisualizePanel />
				<ProgressPanel />
				<OptionsPanel />
			</div>
		</ServerProvider>
	)
}

export default SlicesPage
