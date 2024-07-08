import OptionsPanel from '@renderer/components/OptionsPanel/OptionsPanel'
import styles from './SlicesPage.module.css'
import VisualizePanel from '@renderer/components/VisualizePanel/VisualizePanel'
import ProgressPanel from '@renderer/components/ProgressPanel/Progress'
import { ServerContext } from '@renderer/contexts/ServerContext/ServerContext'
import { CompoundEntry, Entry, OptionsFile } from '@renderer/lib/options'
import { useContext, useState } from 'react'
import { DirectoryContext } from '@renderer/contexts/DirectoryContext/DirectoryContext'
import { join, writeFile } from '@renderer/lib/file'

function SlicesPage(): JSX.Element {
	const { connected, performFetch } = useContext(ServerContext)
	const { directoryPath, refreshDirectory } = useContext(DirectoryContext)

	const [entries] = useState<(Entry | CompoundEntry)[]>([
		new Entry('neuroglancer_json', 'Neuroglancer JSON', '', 'filePath'),
		new OptionsFile()
	])

	const onSubmit = async () => {
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
		performFetch(
			'/slice/',
			{ neuroglancer_json: neuroglancerJSON, options: outputOptions },
			{ method: 'POST' }
		)
	}

	return (
		<div className={styles.slicePage}>
			<VisualizePanel />
			<ProgressPanel />
			<OptionsPanel entries={entries} onSubmit={onSubmit} />
		</div>
	)
}

export default SlicesPage
