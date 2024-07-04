import styles from './CompoundEntry.module.css'

function CompoundEntryElement({ entry, children, title = true, indent = true }): JSX.Element {
	return (
		<>
			{title ? (
				<div className={`${styles.title} poppins-bold option-font-size`}>{entry.label}</div>
			) : null}
			<div className={indent ? styles.indent : ''}>{children}</div>
		</>
	)
}

export default CompoundEntryElement
