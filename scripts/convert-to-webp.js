const fs = require('fs');
const path = require('path');

try {
    const sharp = require('sharp');
} catch (error) {
    console.error('Error: sharp module not found. Please run: npm install');
    process.exit(1);
}

const REPO_DIR = path.join(__dirname, '..');
const SOURCE_DIR = path.join(REPO_DIR, 'blog', 'images', 'original');
const DEST_DIR = path.join(REPO_DIR, 'blog', 'images', 'webp');
const WEBP_QUALITY = 80;

const SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif'];

async function ensureDir(dirPath) {
    if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
    }
}

async function convertImage(inputPath, outputPath) {
    try {
        await ensureDir(path.dirname(outputPath));
        
        await sharp(inputPath)
            .webp({ quality: WEBP_QUALITY })
            .toFile(outputPath);
        
        return { success: true, inputPath, outputPath };
    } catch (error) {
        return { success: false, inputPath, error: error.message };
    }
}

async function processDirectory(sourceDir, destDir) {
    const results = {
        converted: [],
        failed: [],
        skipped: [],
        deleted: []
    };

    if (!fs.existsSync(sourceDir)) {
        console.log(`Source directory does not exist: ${sourceDir}`);
        console.log('Skipping image conversion.');
        return results;
    }

    const sourceFiles = new Map();

    const processPath = async (currentDir, relativeDir = '') => {
        const entries = fs.readdirSync(currentDir, { withFileTypes: true });
        
        for (const entry of entries) {
            const fullPath = path.join(currentDir, entry.name);
            const relativePath = path.join(relativeDir, entry.name);
            
            if (entry.isDirectory()) {
                await processPath(fullPath, relativePath);
            } else if (entry.isFile()) {
                const ext = path.extname(entry.name).toLowerCase();
                
                if (SUPPORTED_FORMATS.includes(ext)) {
                    const baseName = relativePath.replace(/\.[^/.]+$/, '');
                    sourceFiles.set(baseName, fullPath);
                    
                    const outputPath = path.join(
                        destDir, 
                        relativePath.replace(/\.[^/.]+$/, '.webp')
                    );
                    
                    if (fs.existsSync(outputPath)) {
                        const sourceStats = fs.statSync(fullPath);
                        const destStats = fs.statSync(outputPath);
                        
                        if (sourceStats.mtime <= destStats.mtime) {
                            results.skipped.push({
                                inputPath: fullPath,
                                outputPath: outputPath,
                                reason: 'WebP file already exists and is up-to-date'
                            });
                            continue;
                        }
                    }
                    
                    const result = await convertImage(fullPath, outputPath);
                    
                    if (result.success) {
                        results.converted.push(result);
                    } else {
                        results.failed.push(result);
                    }
                }
            }
        }
    };

    await processPath(sourceDir);

    if (fs.existsSync(destDir)) {
        const checkOrphanedFiles = async (currentDir) => {
            const entries = fs.readdirSync(currentDir, { withFileTypes: true });
            
            for (const entry of entries) {
                const fullPath = path.join(currentDir, entry.name);
                
                if (entry.isDirectory()) {
                    await checkOrphanedFiles(fullPath);
                } else if (entry.isFile() && entry.name.toLowerCase().endsWith('.webp')) {
                    const relativePath = path.relative(destDir, fullPath);
                    const baseName = relativePath.replace(/\.webp$/, '');
                    
                    if (!sourceFiles.has(baseName)) {
                        try {
                            fs.unlinkSync(fullPath);
                            results.deleted.push({
                                outputPath: fullPath,
                                reason: 'No corresponding source file found'
                            });
                        } catch (error) {
                            results.failed.push({
                                inputPath: fullPath,
                                error: `Failed to delete orphaned WebP: ${error.message}`
                            });
                        }
                    }
                }
            }
            
            if (currentDir !== destDir) {
                const remainingEntries = fs.readdirSync(currentDir);
                if (remainingEntries.length === 0) {
                    try {
                        fs.rmdirSync(currentDir);
                    } catch (error) {
                        console.warn(`Warning: Could not remove empty directory: ${currentDir}`);
                    }
                }
            }
        };

        await checkOrphanedFiles(destDir);
    }

    return results;
}

async function main() {
    console.log('='.repeat(60));
    console.log('Image to WebP Conversion Tool');
    console.log('='.repeat(60));
    console.log(`Source Directory: ${SOURCE_DIR}`);
    console.log(`Destination Directory: ${DEST_DIR}`);
    console.log(`WebP Quality: ${WEBP_QUALITY}%`);
    console.log('='.repeat(60));
    console.log();
    
    const startTime = Date.now();
    const results = await processDirectory(SOURCE_DIR, DEST_DIR);
    const elapsedTime = ((Date.now() - startTime) / 1000).toFixed(2);
    
    console.log('Conversion Summary:');
    console.log('-'.repeat(60));
    
    if (results.deleted.length > 0) {
        console.log(`\n🗑  Deleted ${results.deleted.length} orphaned WebP file(s):`);
        results.deleted.forEach(r => {
            const relPath = path.relative(REPO_DIR, r.outputPath);
            console.log(`  ${relPath}`);
        });
    }
    
    if (results.converted.length > 0) {
        console.log(`\n✓ Successfully converted ${results.converted.length} image(s):`);
        results.converted.forEach(r => {
            const relPath = path.relative(REPO_DIR, r.inputPath);
            const relOutput = path.relative(REPO_DIR, r.outputPath);
            console.log(`  ${relPath} → ${relOutput}`);
        });
    }
    
    if (results.skipped.length > 0) {
        console.log(`\n⊘ Skipped ${results.skipped.length} image(s) (already up-to-date):`);
        results.skipped.forEach(r => {
            const relPath = path.relative(REPO_DIR, r.inputPath);
            console.log(`  ${relPath} (${r.reason})`);
        });
    }
    
    if (results.failed.length > 0) {
        console.log(`\n✗ Failed to convert ${results.failed.length} image(s):`);
        results.failed.forEach(r => {
            const relPath = path.relative(REPO_DIR, r.inputPath);
            console.log(`  ${relPath}: ${r.error}`);
        });
    }
    
    console.log();
    console.log('-'.repeat(60));
    console.log(`Total time: ${elapsedTime}s`);
    console.log('='.repeat(60));
    
    if (results.failed.length > 0) {
        process.exit(1);
    }
}

if (require.main === module) {
    main().catch(error => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
}

module.exports = { processDirectory, convertImage };