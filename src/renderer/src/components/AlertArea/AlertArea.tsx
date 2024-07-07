import { AlertMessageType } from '@renderer/contexts/AlertContext/AlertContext'
import styles from './AlertArea.module.css'
import Alert from './components/Alert/Alert'

function AlertArea({ alerts }: { alerts: AlertMessageType[] }): JSX.Element {
	return (
		<div className={styles.alertArea}>
			{alerts.map((alert, index) => (
				<Alert key={index} message={alert.message} type={alert.type} />
			))}
		</div>
	)
}

export default AlertArea
