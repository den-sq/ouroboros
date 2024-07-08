import { CompoundEntry, Entry } from '@renderer/lib/options'
import Header from '../Header/Header'
import OptionEntry from './components/OptionEntry/OptionEntry'
import OptionSubmit from './components/OptionSubmit/OptionSubmit'
import styles from './OptionsPanel.module.css'
import CompoundEntryElement from './components/CompoundEntry/CompoundEntry'

function OptionsPanel({
	entries,
	onSubmit
}: {
	entries: (Entry | CompoundEntry)[]
	onSubmit: () => Promise<void>
}): JSX.Element {
	const entryElement = entries.flatMap((entryObject) => {
		if (entryObject instanceof Entry) return entryToElement(entryObject)
		else return compoundEntryToElement(entryObject, false, false)
	})

	const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
		e.preventDefault()

		await onSubmit()
	}

	return (
		<div className="panel">
			<form className={styles.form} method="post" onSubmit={handleSubmit}>
				<Header text={'Options'} />
				{entryElement}
				<OptionSubmit />
			</form>
		</div>
	)
}

function compoundEntryToElement(compoundEntry: CompoundEntry, indent = true, title = true) {
	return (
		<CompoundEntryElement
			key={compoundEntry.name}
			entry={compoundEntry}
			indent={indent}
			title={title}
		>
			{compoundEntry.entries.map((entry) => {
				if (entry instanceof Entry) return entryToElement(entry)
				else return compoundEntryToElement(entry)
			})}
		</CompoundEntryElement>
	)
}

function entryToElement(entry: Entry) {
	return <OptionEntry key={entry.name} entry={entry} />
}

export default OptionsPanel
