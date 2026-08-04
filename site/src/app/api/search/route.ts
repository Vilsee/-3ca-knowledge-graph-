import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('q');
  
  if (!query) return NextResponse.json({ results: [] });

  try {
    // Escape query safely
    const safeQuery = query.replace(/"/g, '\\"');
    const scriptPath = path.resolve(process.cwd(), '../scripts/run_search.py');
    const { stdout } = await execAsync(`python "${scriptPath}" "${safeQuery}" 10`, { 
        cwd: path.resolve(process.cwd(), '../')
    });
    
    // Parse the output string that starts with '[' and ends with ']'
    const jsonMatch = stdout.match(/\[[\s\S]*\]/);
    if (jsonMatch) {
      return NextResponse.json({ results: JSON.parse(jsonMatch[0]) });
    } else {
      throw new Error("Invalid output from python: " + stdout);
    }
  } catch (error) {
    console.error(error);
    return NextResponse.json({ results: [], error: String(error) }, { status: 500 });
  }
}
