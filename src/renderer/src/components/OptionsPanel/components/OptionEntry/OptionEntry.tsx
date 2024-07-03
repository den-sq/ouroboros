import { useRef, useEffect, useState, ChangeEvent } from 'react'
import styles from './OptionEntry.module.css'

const MIN_WIDTH = 25
const LABEL_GAP = 15

// Types: number, string, boolean, draggable

function OptionEntry({ label, initialValue, inputType, minWidth = MIN_WIDTH }): JSX.Element {
	const inputRef = useRef<HTMLInputElement>(null)
	const labelRef = useRef<HTMLDivElement>(null)
	const [labelWidth, setLabelWidth] = useState(0)

	const inputName = label.toLowerCase().replace(' ', '-')

	let htmlInputType = 'text'

	switch (inputType) {
		case 'number':
			htmlInputType = 'number'
			break
		case 'string':
			htmlInputType = 'text'
			break
		case 'boolean':
			htmlInputType = 'checkbox'
			break
		case 'draggable':
			htmlInputType = 'text'
			break
		default:
			break
	}

	useEffect(() => {
		if (inputType === 'boolean') return

		if (labelRef.current) {
			const label = labelRef.current
			// Measure and store label width
			setLabelWidth(label.offsetWidth + LABEL_GAP)
		}

		if (inputRef.current) {
			const input = inputRef.current

			// Create a temporary span to measure text width
			const tempSpan = document.createElement('span')

			// Match input font size and family
			tempSpan.style.fontSize = getComputedStyle(input).fontSize
			tempSpan.style.fontFamily = getComputedStyle(input).fontFamily
			tempSpan.style.visibility = 'hidden' // Hide span
			tempSpan.textContent = initialValue
			document.body.appendChild(tempSpan)

			// Set input width based on temp span width, with a minimum width
			input.style.width = `${Math.max(tempSpan.offsetWidth, minWidth)}px`
			document.body.removeChild(tempSpan)
		}
	}, [initialValue, minWidth])

	const onChange = (e: ChangeEvent<HTMLInputElement>) => {
		if (inputType === 'boolean') return
		if (!inputRef.current) return

		const target = e.target
		const parentWidth = target.parentElement?.offsetWidth || 0
		const maxWidth = parentWidth - labelWidth

		target.style.width = `${minWidth}px` // Reset width to minimum before calculating new width
		target.style.width = `${Math.min(target.scrollWidth, maxWidth)}px`
	}

	return (
		<div className={`${styles.optionEntry} poppins-medium`}>
			<div ref={labelRef} className={`${styles.optionLabel} option-font-size`}>
				{label}
			</div>
			<input
				name={inputName}
				ref={inputRef}
				type={htmlInputType}
				className={styles.optionInput}
				defaultValue={initialValue}
				onChange={onChange}
			/>
		</div>
	)
}

export default OptionEntry
