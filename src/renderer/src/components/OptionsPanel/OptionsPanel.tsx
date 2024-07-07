import { CompoundEntry, Entry, OptionsFile } from '@renderer/lib/options'
import Header from '../Header/Header'
import OptionEntry from './components/OptionEntry/OptionEntry'
import OptionSubmit from './components/OptionSubmit/OptionSubmit'
import styles from './OptionsPanel.module.css'
import CompoundEntryElement from './components/CompoundEntry/CompoundEntry'
import { join, writeFile } from '@renderer/lib/file'
import { useContext, useState } from 'react'
import { ServerContext } from '@renderer/contexts/ServerContext/ServerContext'
import { DirectoryContext } from '@renderer/contexts/DirectoryContext/DirectoryContext'

function OptionsPanel(): JSX.Element {
	const { connected, useFetch } = useContext(ServerContext)
	const { directoryPath, refreshDirectory } = useContext(DirectoryContext)

	const [query, setQuery] = useState({})
	const [runFetch, setRunFetch] = useState(false)

	useFetch('/slice/', query, runFetch, { method: 'POST' })

	const entries: (Entry | CompoundEntry)[] = [
		new Entry('neuroglancer_json', 'Neuroglancer JSON', '', 'filePath'),
		new OptionsFile()
	]

	const entryElement = entries.flatMap((entryObject) => {
		if (entryObject instanceof Entry) return entryToElement(entryObject)
		else return compoundEntryToElement(entryObject, false, false)
	})

	const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
		e.preventDefault()

		if (!connected) {
			return
		}

		const optionsObject = entries[1].toObject()

		const outputFolder = await join(directoryPath, optionsObject['output_file_folder'])

		// Add the absolute output folder to the options object
		optionsObject['output_file_folder'] = outputFolder

		const outputName = optionsObject['output_file_name']
		const neuroglancerJSON = await join(directoryPath, entries[0].toObject() as string)

		// Validate options
		if (
			!optionsObject['output_file_folder'] ||
			!outputName ||
			!entries[0].toObject() ||
			optionsObject['output_file_folder'] === '' ||
			outputName === '' ||
			entries[0].toObject() === ''
		) {
			return
		}

		const modifiedName = `${outputName}-options-slice.json`

		// Save options to file
		await writeFile(outputFolder, modifiedName, JSON.stringify(optionsObject, null, 4))

		refreshDirectory()

		const outputOptions = await join(outputFolder, modifiedName)

		// Run the slice generation
		setQuery({ neuroglancer_json: neuroglancerJSON, options: outputOptions })
		setRunFetch(true)
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
