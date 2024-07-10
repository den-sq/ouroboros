import { CompoundEntry, Entry } from '@renderer/lib/options'
import Header from '../Header/Header'
import OptionEntry from './components/OptionEntry/OptionEntry'
import OptionSubmit from './components/OptionSubmit/OptionSubmit'
import styles from './OptionsPanel.module.css'
import CompoundEntryElement from './components/CompoundEntry/CompoundEntry'

function OptionsPanel({
	entries,
	onSubmit,
	onEntryChange
}: {
	entries: (Entry | CompoundEntry)[]
	onSubmit: () => Promise<void>
	onEntryChange?: (entry: Entry) => void
}): JSX.Element {
	if (onEntryChange === undefined) {
		onEntryChange = () => {}
	}

	const entryElement = entries.flatMap((entryObject) => {
		if (entryObject instanceof Entry) return entryToElement(entryObject, onEntryChange)
		else return compoundEntryToElement(entryObject, onEntryChange, false, false)
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

function compoundEntryToElement(
	compoundEntry: CompoundEntry,
	onEntryChange: (entry: Entry) => void,
	indent = true,
	title = true
) {
	return (
		<CompoundEntryElement
			key={compoundEntry.name}
			entry={compoundEntry}
			indent={indent}
			title={title}
		>
			{compoundEntry.entries.map((entry) => {
				if (entry instanceof Entry) return entryToElement(entry, onEntryChange)
				else return compoundEntryToElement(entry, onEntryChange)
			})}
		</CompoundEntryElement>
	)
}

function entryToElement(entry: Entry, onEntryChange: (entry: Entry) => void) {
	return <OptionEntry key={entry.name} entry={entry} onEntryChange={onEntryChange} />
}

export default OptionsPanel
