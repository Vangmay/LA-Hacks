// TestabilityChip.jsx — Chip for testability status
import Chip from './Chip'

export default function TestabilityChip({ testability }) {
  if (testability === 'testable')
    return <Chip color="#22C55E" bg="rgba(20,83,45,0.13)" border="#22C55E">TESTABLE</Chip>
  if (testability === 'theoretical')
    return <Chip color="#F59E42" bg="rgba(120,53,15,0.13)" border="#F59E42">THEORETICAL</Chip>
  return <Chip color="#6B7280">UNKNOWN</Chip>
}
