export type CompoundValueType = { [key: string]: CompoundValueType | ValueType } | ValueType
export type ValueType = number | string | boolean
export type EntryValueType = 'number' | 'string' | 'boolean' | 'filePath'

export class Entry {
	name: string
	label: string
	value: ValueType
	type: EntryValueType
	options?: string[]

	constructor(
		name: string,
		label: string,
		value: ValueType,
		type: EntryValueType,
		options?: string[]
	) {
		this.name = name
		this.label = label
		this.value = value
		this.type = type
		this.options = options
	}

	setValue(value: CompoundValueType) {
		if (typeof value === 'object') return

		if (typeof value !== typeof this.value) return

		this.value = value
	}

	setValueFromEntry(entry: Entry | CompoundEntry) {
		if (entry instanceof Entry) this.setValue(entry.value)
	}

	toObject() {
		return this.value
	}
}

export class CompoundEntry {
	name: string
	label: string
	entries: (Entry | CompoundEntry)[]
	entryMap: { [key: string]: Entry | CompoundEntry } = {}

	constructor(name: string, label: string, entries: (Entry | CompoundEntry)[]) {
		this.name = name
		this.label = label
		this.entries = entries

		// Create the entry map
		for (const entry of entries) {
			this.entryMap[entry.name] = entry
		}
	}

	setValue(value: CompoundValueType) {
		if (typeof value !== 'object') return

		for (const [name, val] of Object.entries(value)) {
			if (!(name in this.entryMap)) return

			this.entryMap[name].setValue(val)
		}
	}

	setValueFromEntry(entry: Entry | CompoundEntry) {
		if (entry instanceof Entry) return

		for (const _entry of entry.entries) {
			if (!(_entry.name in this.entryMap)) return

			this.entryMap[_entry.name].setValueFromEntry(_entry)
		}
	}

	toObject(includeSelf = false) {
		const result = {}

		for (const entry of this.entries) {
			result[entry.name] = entry.toObject()
		}

		if (includeSelf) {
			const includeSelfResult = {}
			includeSelfResult[this.name] = result
			return includeSelfResult
		}

		return result
	}

	getEntries() {
		return this.entries
	}
}

export class SliceOptionsFile extends CompoundEntry {
	constructor(values: CompoundValueType = {}) {
		super('options', 'Options File', [
			new Entry('neuroglancer_json', 'Neuroglancer JSON', '', 'filePath'),
			new Entry('neuroglancer_image_layer', 'Neuroglancer Image Layer', '', 'string'),
			new Entry(
				'neuroglancer_annotation_layer',
				'Neuroglancer Annotation Layer',
				'',
				'string'
			),
			new Entry('slice_width', 'Slice Width', 120, 'number'),
			new Entry('slice_height', 'Slice Height', 120, 'number'),
			new Entry('output_file_folder', 'Output File Folder', './', 'filePath'),
			new Entry('output_file_name', 'Output File Name', 'sample', 'string'),
			new Entry('dist_between_slices', 'Distance Between Slices', 1, 'number'),
			new Entry('flush_cache', 'Flush CloudVolume Cache', false, 'boolean'),
			new Entry('connect_start_and_end', 'Connect Endpoints', false, 'boolean'),
			new CompoundEntry('bounding_box_params', 'Bounding Box Parameters', [
				new Entry('max_depth', 'Max Depth', 10, 'number'),
				new Entry('target_slices_per_box', 'Target Slices per Box', 128, 'number')
			]),
			new Entry('make_single_file', 'Output Single File', true, 'boolean'),
			new Entry('max_ram_gb', 'Max RAM (GB) (0 = no limit)', 0, 'number')
		])

		this.setValue(values)
	}
}

export class BackprojectOptionsFile extends CompoundEntry {
	constructor(values: CompoundValueType = {}) {
		super('options', 'Options File', [
			new Entry('straightened_volume_path', 'Straightened Volume File', '', 'filePath'),
			new Entry('config_path', 'Slice Configuration File', '', 'filePath'),
			new Entry('slice_width', 'Slice Width', 120, 'number'),
			new Entry('slice_height', 'Slice Height', 120, 'number'),
			new Entry('output_file_folder', 'Output File Folder', './', 'filePath'),
			new Entry('output_file_name', 'Output File Name', 'sample', 'string'),
			new Entry('dist_between_slices', 'Distance Between Slices', 1, 'number'),
			new Entry('flush_cache', 'Flush CloudVolume Cache', false, 'boolean'),
			new Entry('connect_start_and_end', 'Connect Endpoints', false, 'boolean'),
			new Entry('backproject_min_bounding_box', 'Output Min Bounding Box', true, 'boolean'),
			new Entry('make_backprojection_binary', 'Binary Backprojection', false, 'boolean'),
			new Entry('backprojection_compression', 'Backprojection Compression', 'zstd', 'string'),
			new Entry('make_single_file', 'Output Single File', true, 'boolean'),
			new Entry('max_ram_gb', 'Max RAM (GB) (0 = no limit)', 0, 'number')
		])

		this.setValue(values)
	}
}
